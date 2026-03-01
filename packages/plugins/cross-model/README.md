# Cross-Model Plugin

Cross-model consultation via OpenAI Codex, with context injection for mid-conversation evidence gathering and code-level credential enforcement. Future: persistent cross-model learning from consultation resolutions.

## What this plugin provides

- `/codex` skill — single-turn and multi-turn Codex consultations
- `/dialogue` skill — orchestrated multi-turn consultation with parallel context gathering (`--posture`, `--turns`, `--profile`, `--plan`)
- `/consultation-stats` skill — analytics dashboard for consultations, dialogues, and security events
- `codex-dialogue` subagent — extended multi-turn dialogue with convergence detection
- `codex-reviewer` agent — single-turn code review via Codex
- `context-gatherer-code` agent — pre-dialogue codebase explorer launched by `/dialogue`
- `context-gatherer-falsifier` agent — pre-dialogue assumption tester launched by `/dialogue`
- Context injection MCP server — mid-conversation evidence gathering for Codex dialogues
- Consultation contract and named profiles (normative reference)
- Context injection contract (normative reference)
- PreToolUse credential enforcement hook — blocks dispatch if secrets detected
- PostToolUse consultation event log at `~/.claude/.codex-events.jsonl`
- Opt-in nudge hook — suggests `/codex` after repeated Bash failures (`CROSS_MODEL_NUDGE=1`)
- Auto-configured MCP connections (Codex + context injection)

## Prerequisites

1. Codex CLI: `npm install -g @openai/codex`
2. Auth: `codex login` (or set `OPENAI_API_KEY`)
3. `uv` (for context injection server): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Installation

```bash
claude plugin install cross-model@turbo-mode
```

Restart Claude Code after installing.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CROSS_MODEL_NUDGE` | unset | Set to `1` to enable opt-in failure nudge hook |

## Enforcement model

The PreToolUse hook runs **tiered credential detection** on every outbound prompt:

| Tier | Behavior | Examples |
|------|---------|---------|
| Strict | Hard-block | AWS keys, PEM private keys, JWT tokens |
| Contextual | Block unless example/placeholder language nearby | GitHub PATs, OpenAI keys, Bearer tokens |
| Broad | Shadow telemetry only | Generic credential assignments |

**Scope enforcement:** outbound prompts are checked against a `scope_envelope` (allowed roots and source classes) before delegation to Codex. Scope breaches terminate the dialogue with `termination_reason: scope_breach`.

**Fail-closed design:** hook errors block the call (PreToolUse). Hook process crashes are fail-open by OS exit code semantics — this is a known limitation documented below.

**Fail-open paths (by design):**
- Hook process crashes (OS-level exit — not caught by the script's exception handler)
- Plugin not installed or disabled
- Broad-tier matches (logged only, not blocked)

## Escalation to wrapper MCP

This hook-based model is proportionate for the **accidental-credential threat model**. If the threat model changes to adversarial exfiltration (zero-tolerance), escalate to a wrapper MCP server that enforces at the transport level.

Escalation triggers (log these, evaluate quarterly):
- Block rate > 5% over 30 days (suggests patterns need tuning or threat model changed)
- Discovery of a false negative that hooks would have caught with tighter patterns
- User-reported intentional credential exfiltration attempt

## Event log

`~/.claude/.codex-events.jsonl` — one JSON object per line:

| Event | When | Fields |
|-------|------|--------|
| `block` | PreToolUse blocks | `ts`, `event`, `tool`, `session_id`, `prompt_length`, `reason` |
| `shadow` | Broad-tier match | same as block |
| `consultation` | PostToolUse | `ts`, `event`, `tool`, `session_id`, `prompt_length`, `result_length`, `thread_id_present` |
| `dialogue_outcome` | `/dialogue` Step 7 | `schema_version`, `consultation_id`, `thread_id`, `session_id`, `event`, `ts`, `posture`, `turn_count`, `turn_budget`, `profile_name`, `mode`, `converged`, `convergence_reason_code`, `termination_reason`, `resolved_count`, `unresolved_count`, `emerged_count`, `seed_confidence`, `low_seed_confidence_reasons`, `assumption_count`, `no_assumptions_fallback`, gatherer metrics, scope envelope, nullable planning/provenance fields |
| `consultation_outcome` | `/codex` post-diagnostics | `schema_version`, `consultation_id`, `thread_id`, `session_id`, `event`, `ts`, `posture`, `turn_count`, `turn_budget`, `profile_name`, `mode`, `converged`, `termination_reason` |

`dialogue_outcome` and `consultation_outcome` events use `schema_version` for forward compatibility. See `docs/plans/2026-02-19-cross-model-plugin-enhancements.md` §4.4 for version semantics.
