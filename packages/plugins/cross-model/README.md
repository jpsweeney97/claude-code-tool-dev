# Cross-Model Plugin

> **v3.0.0** · MIT · Python ≥3.11 · Requires Codex CLI; `/dialogue` also uses `uv`, `git`, and the bundled `context-injection` helper

Cross-model consultation via OpenAI Codex. Claude consults an independent model for second opinions on architecture, debugging, code review, plans, and decisions — then independently assesses every response before presenting it to the user. Claude is always primary; Codex is always advisory.

The plugin includes credential enforcement (tiered detection on every outbound prompt), scope envelopes (limiting what Codex can see), context injection (mid-conversation evidence gathering from the codebase), and a full analytics pipeline.

## What Problem Does This Solve?

A single model working alone has blind spots. It can't challenge its own assumptions, catch its own biases, or notice when it's pattern-matching to familiar solutions instead of reasoning about the actual problem. The cross-model plugin gives Claude a structured way to consult an independent model — not to defer to it, but to *pressure-test its own thinking*. The resulting consultations produce higher-quality decisions because disagreements surface hidden assumptions and force explicit reasoning.

## Quick Start

Prerequisites:

```bash
npm install -g @openai/codex   # Codex CLI
codex login                     # Or set OPENAI_API_KEY
```

Additional runtime requirements for `/dialogue`:

- `uv` must be available because the bundled `context-injection` MCP server is launched through `uv run`
- `git` must be on `PATH`
- `context-injection` is POSIX-only (`macOS`, `Linux`, `WSL`)
- Start Claude from the repository you want `/dialogue` to inspect; `.mcp.json` exports `REPO_ROOT=${PWD}` to the helper

Install:

```bash
claude plugin install cross-model@turbo-mode
```

Quick consultation:

```
/codex Is this the right approach for handling auth token refresh?
```

Deep multi-turn dialogue with context gathering:

```
/dialogue "Should we use WebSockets or SSE for real-time updates?" --profile deep-review
```

Autonomous Codex execution (sandboxed):

```
/delegate "Refactor the auth module to use dependency injection"
```

## How It Works

### Architecture

```
User: /codex or /dialogue
         │
         ▼
    ┌─────────────┐     ┌──────────────────┐
    │  Skill       │     │  Gatherer Agents  │ (/dialogue only)
    │  (/codex or  │◄────│  code + falsifier │
    │   /dialogue) │     └──────────────────┘
    │              │
    │  Briefing    │
    │  Assembly    │
    └──────┬──────┘
           │
    ┌──────▼──────┐     ┌─────────────────┐
    │  codex_guard │────►│  Event Log       │
    │  (PreToolUse)│     │  (.codex-events  │
    │  Credential  │     │   .jsonl)        │
    │  Detection   │     └─────────────────┘
    └──────┬──────┘
           │ (if clean)
    ┌──────▼──────┐     ┌─────────────────┐
    │  Codex MCP   │◄───►│  Context         │
    │  Server      │     │  Injection MCP   │
    │  (stdio)     │     │  (scouting loop) │
    └──────┬──────┘     └─────────────────┘
           │
    ┌──────▼──────┐
    │  codex_guard │
    │  (PostToolUse│
    │   logging)   │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Claude      │
    │  Independent │
    │  Assessment  │
    └─────────────┘
```

Key design properties:

- **Claude is always primary** — Codex responses are assessed independently before presenting to the user
- **Fail-closed credential detection** — Hook errors on PreToolUse block the call, preventing accidental secret exfiltration
- **Scope envelopes** — Each consultation declares allowed roots and source classes; breaches terminate the dialogue
- **Analytics by default** — Every consultation emits structured telemetry for observability

### Four Entrypoints

| Entrypoint | Use Case | Turns | Context Gathering | Profiles |
|------------|----------|-------|-------------------|----------|
| `/codex` | Quick second opinion | 1-2 direct; may delegate longer sessions | None directly; can delegate to `codex-dialogue` | No |
| `/dialogue` | Deep consultation | 1-15 (default 8) | Parallel gatherer agents + context injection in `server_assisted` mode | Yes |
| `/delegate` | Autonomous execution | 1 | None | No |
| `/consultation-stats` | Local analytics and reporting | N/A | Reads event log only | No |

`/codex` is lightweight: it sends a prompt to Codex, relays the response, and emits analytics. It decides between inline execution (1-2 turns) and subagent delegation (3+ turns) based on topic complexity. When it delegates, the work runs through `codex-dialogue`; operational continuation then follows the delegated subagent context rather than only a raw `threadId`.

`/delegate` hands a task to Codex for autonomous execution in a sandboxed environment. Unlike `/codex` and `/dialogue` (which sanitize prompts to prevent credential exfiltration), `/delegate` relies on sandbox containment — Codex runs in a restricted environment where network access and filesystem writes are controlled by the sandbox provider. Two pre-flight gates enforce safety: the **clean-tree gate** requires a clean git working tree (so unwanted changes can be reverted), and the **secret-file gate** rejects tasks that reference known secret files (`.env`, credentials, key files).

`/dialogue` is a full 7-step pipeline:

1. **Step 0** (optional, `--plan` flag) — Question decomposition: extracts assumptions, key terms, ambiguities
2. **Step 1** — Resolve testable assumptions with IDs (A1, A2...)
3. **Step 2** — Launch two gatherer agents in parallel (120s timeout each)
4. **Step 3** — Deterministic briefing assembly from prefix-tagged lines (credential sanitization, dedup, provenance validation)
5. **Step 4** — Health check (min 8 citations, min 5 unique files) and seed confidence scoring
6. **Step 5** — Delegate to `codex-dialogue` agent with scope envelope and briefing
7. **Step 6-7** — Run the delegated session in `server_assisted` mode when context injection is available, or fall back early to `manual_legacy` when the agent cannot establish a successful initial `process_turn`; then present synthesis and emit analytics with the actual `mode`

### Named Profiles

Profiles preconfigure posture, turn budget, and reasoning effort for common consultation patterns:

| Profile | Posture | Turns | Use Case |
|---------|---------|-------|----------|
| `quick-check` | collaborative | 1 | Fast sanity check |
| `collaborative-ideation` | collaborative | 6 | Brainstorming together |
| `exploratory` | exploratory | 6 | Open-ended investigation |
| `deep-review` | evaluative | 8 | Thorough analysis |
| `code-review` | evaluative | 4 | Focused code review |
| `adversarial-challenge` | adversarial | 6 | Stress-test an approach |
| `planning` | comparative | 8 | Compare approaches |
| `decision-making` | comparative | 6 | Choose between options |
| `debugging` | multi-phase | 7 | Exploratory → evaluative → collaborative |

Usage: `/dialogue "question" --profile deep-review`

Local overrides: create `consultation-profiles.local.yaml` (gitignored) alongside the profiles file.

### The Event Log

All telemetry flows to `~/.claude/.codex-events.jsonl`:

| Event | Source | When |
|-------|--------|------|
| `block` | `codex_guard.py` (PreToolUse) | Credential detected — dispatch blocked |
| `shadow` | `codex_guard.py` (PreToolUse) | Broad-tier match — logged only, not blocked |
| `consultation` | `codex_guard.py` (PostToolUse) | Raw Codex tool call completed |
| `consultation_outcome` | `emit_analytics.py` | `/codex` skill result with diagnostics |
| `dialogue_outcome` | `emit_analytics.py` | `/dialogue` skill result with full pipeline metrics |
| `delegation_outcome` | `emit_analytics.py` | `/delegate` skill result with sandbox mode and gate status |

Schema versioning: `0.1.0` → `0.2.0` (provenance) → `0.3.0` (planning). Forward-compatible — older readers skip unknown fields.

Dialogue analytics also record the actual execution `mode` (`server_assisted` or `manual_legacy`), which matters when interpreting scout-related metrics.

## Skills

### `/codex [-m model] [-s sandbox] [-a approval] [-t reasoning] [PROMPT]`

Single-turn or short multi-turn Codex consultation. Argument parsing is deterministic — rejects unknown flags and invalid enum values. After relay, captures non-secret diagnostics and emits a `consultation_outcome` analytics event.

### `/dialogue "question" [-p posture] [-n turns] [--profile name] [--plan]`

Orchestrated multi-turn consultation with parallel context gathering. The `--plan` flag enables question decomposition (Claude-local, no Codex) before dispatching. The delegated `codex-dialogue` agent starts in `server_assisted` mode and can fall back to `manual_legacy` before the first successful `process_turn`. Emits a `dialogue_outcome` event with full pipeline metrics including gatherer line counts, provenance stats, scope fingerprints, seed confidence, and execution `mode`.

### `/delegate [PROMPT]`

Autonomous Codex execution. Delegates a task to Codex for sandboxed execution rather than consultation. Uses a narrower trust model than `/codex` and `/dialogue`: instead of prompt sanitization, it relies on sandbox containment. Pre-flight gates: clean git working tree (dirty tree blocks execution) and secret-file rejection (references to `.env`, credentials, or key files block execution). Emits a `delegation_outcome` analytics event.

### `/consultation-stats [--period N] [--type TYPE]`

Analytics dashboard. Reads the event log and presents: usage counts, dialogue quality (convergence rates, posture effectiveness), context quality (seed confidence, gatherer metrics), and security events (blocks, shadows by tier).

## Agents

| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| `codex-dialogue` | opus | Extended multi-turn Codex conversation with convergence detection. 7-step scouting loop via context injection. Emits `<!-- pipeline-data -->` epilogue. | Bash, Read, Glob, Grep, Codex MCP, Context Injection MCP |
| `codex-reviewer` | opus | Single-turn code review. Reads git diff, assembles briefing, max 2 Codex turns. Diff tiers: ≤500 full, 501-1500 summarize, >1500 hard cap. | Bash, Read, Glob, Grep, Codex MCP |
| `context-gatherer-code` | sonnet | Pre-dialogue codebase explorer. Emits `CLAIM` and `OPEN` tagged lines. Searches code, tests, config. Max 8 files, 40-line cap. | Glob, Grep, Read |
| `context-gatherer-falsifier` | sonnet | Pre-dialogue assumption tester. Emits `COUNTER`, `CONFIRM`, `OPEN` tagged lines. Tests assumptions against codebase evidence. Max 3 COUNTERs. | Glob, Grep, Read |

## Enforcement Model

The PreToolUse hook runs **tiered credential detection** on every outbound prompt:

| Tier | Behavior | Examples |
|------|---------|---------|
| Strict | Hard-block | AWS keys, PEM private keys, JWT tokens |
| Contextual | Block unless example/placeholder language nearby | GitHub PATs, OpenAI keys, Bearer tokens |
| Broad | Shadow telemetry only | Generic credential assignments |

**Scope enforcement:** Outbound prompts are checked against a `scope_envelope` (allowed roots and source classes) before delegation to Codex. Scope breaches terminate the dialogue with `termination_reason: scope_breach`.

**Fail-closed design:** Hook errors block the call (PreToolUse). Hook process crashes are fail-open by OS exit code semantics — this is a known limitation.

### Escalation to Wrapper MCP

This hook-based model is proportionate for the **accidental-credential threat model**. If the threat model changes to adversarial exfiltration, escalate to a wrapper MCP server that enforces at the transport level.

Escalation triggers (evaluate quarterly):
- Block rate > 5% over 30 days
- Discovery of a false negative that hooks would have caught with tighter patterns
- User-reported intentional credential exfiltration attempt

## MCP Servers

Two MCP servers are auto-configured by the plugin (no manual setup):

| Server | Transport | Purpose |
|--------|-----------|---------|
| `codex` | stdio (`codex mcp-server`) | Provides `codex` and `codex-reply` tools for Codex communication |
| `context-injection` | stdio (`uv run --directory ${CLAUDE_PLUGIN_ROOT}/context-injection python -m context_injection`) | Mid-conversation evidence gathering: scouting loop, claim verification, codebase reads |

The context injection server lives in `packages/plugins/cross-model/context-injection/`. It is the canonical helper package used by `/dialogue`, with 991 tests in its own `tests/` directory.

Runtime wiring:

- `CODEX_SANDBOX=seatbelt` is set automatically for the `codex` server to prevent a macOS Codex CLI panic
- `REPO_ROOT=${PWD}` is passed to `context-injection`, so the helper inspects the repository from which Claude was launched
- `context-injection` requires `git` and a POSIX host at startup

## Hook Configuration

| Event | Matcher | Script | Timeout | Behavior |
|-------|---------|--------|---------|----------|
| `PreToolUse` | `codex\|codex-reply` | `codex_guard.py` | — | Credential detection; exit 2 blocks |
| `PostToolUse` | `codex\|codex-reply` | `codex_guard.py` | — | Logs `consultation` event; never blocks |
| `PostToolUseFailure` | `Bash` | `nudge_codex.py` | — | Opt-in (`CROSS_MODEL_NUDGE=1`): after 3 consecutive Bash failures, suggests `/codex` |

## Script Reference

| Script | Purpose |
|--------|---------|
| `codex_guard.py` | Single script for both PreToolUse and PostToolUse. Dispatches on `hook_event_name`. Tiered credential detection (strict/contextual/broad). Logs events to JSONL. |
| `nudge_codex.py` | PostToolUseFailure hook. Tracks failure count per session in temp file with `fcntl.flock`. After 3 failures, injects `additionalContext` nudge. |
| `emit_analytics.py` | Deterministic analytics emitter. Parses synthesis text (regex, no LLM), validates fields, appends to event log. Handles both `dialogue_outcome` and `consultation_outcome` events. Schema auto-bumps. |
| `compute_stats.py` | Analytics computation. CLI: `--period` (7/30/all), `--type` (security/dialogue/consultation/delegation/all). 5 report sections with section-inclusion matrix. |
| `read_events.py` | JSONL reader and event classifier. Skips malformed lines silently. Returns `(events, skipped_count)`. |
| `stats_common.py` | Shared analytics primitives: period filtering, observed-denominator averaging, timestamp parsing (rejects non-UTC). |

## Reference Files

| File | Purpose |
|------|---------|
| `references/consultation-contract.md` | 17-section normative contract: safety pipeline, briefing structure, governance rules (7 locked), delegation envelope, transport adapter, profiles, learning card retrieval. |
| `references/consultation-profiles.yaml` | 9 named profiles with posture, turns, and reasoning effort. Version 0.2.0. |
| `references/context-injection-contract.md` | Protocol contract for context injection MCP server. |
| `skills/dialogue/references/tag-grammar.md` | Grammar spec for prefix-tagged lines: 8 parse rules, 5 contradiction types, 9-step assembly processing. |

## Tests

Plugin-local suite: **160 tests across 8 files**.

| Test File | Coverage Area |
|-----------|--------------|
| `test_codex_delegate.py` | `/delegate` adapter pipeline, validation, gates, JSONL parsing, analytics invariants |
| `test_codex_guard.py` | PreToolUse / PostToolUse hook behavior, traversal limits, credential blocking |
| `test_compute_stats.py` | analytics aggregation, delegation metrics, section inclusion, JSON flag compatibility |
| `test_credential_scan.py` | strict/contextual/broad secret detection taxonomy |
| `test_emit_analytics.py` | synthesis parsing, posture validation, schema/version behavior |
| `test_event_log.py` | log append semantics, timestamp format, session ID handling |
| `test_read_events.py` | event classification and required-field validation |
| `test_secret_taxonomy.py` | pattern compilation and taxonomy consistency |

The context injection server has 991 tests in `packages/plugins/cross-model/context-injection/tests/`.

```bash
cd packages/plugins/cross-model && uv run pytest
```

To inspect the collected plugin-local tests without running them:

```bash
uv run pytest --co -q tests
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CROSS_MODEL_NUDGE` | unset | Set to `1` to enable the opt-in failure nudge hook |
| `CODEX_SANDBOX` | `seatbelt` | Set automatically by MCP config to prevent macOS Codex CLI panic |
| `REPO_ROOT` | `${PWD}` via `.mcp.json` | Repository root consumed by the bundled `context-injection` helper |
| `OPENAI_API_KEY` | — | Required if not using `codex login` |

## Known Limitations

1. **Hook process crash is fail-open** — If `codex_guard.py` crashes at the OS level (not a Python exception), Claude Code treats the non-zero exit as "no output" and allows the call. This is an OS-level constraint, not a design choice.
2. **Broad-tier matches are logged only** — Generic credential assignments (e.g., `password = "..."`) are tracked via shadow telemetry but never blocked. This is by design to avoid false positives on example code.
3. **Plugin disabled = no enforcement** — If the plugin is uninstalled or disabled, credential detection stops entirely. There is no fallback enforcement mechanism.
4. **Helper tests are separate from plugin-root tests** — Deep helper validation runs from `packages/plugins/cross-model/context-injection`, not from `packages/plugins/cross-model/tests`.
5. **Codex CLI dependency** — Requires `@openai/codex` npm package installed globally. Version compatibility is not pinned.
6. **`episode_id` field is reserved** — The `dialogue_outcome` event includes a nullable `episode_id` field for a planned cross-model learning system. Not yet populated.
