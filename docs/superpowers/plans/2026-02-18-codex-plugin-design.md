# Codex Plugin — Design Exploration

**Date:** 2026-02-18
**Status:** Design complete — ready for planning
**Source:** Design conversation + 3 Codex consultations (adversarial ×1, evaluative ×2 parallel)

---

## What exists today

Assets that would be packaged into `packages/plugins/codex/`:

| Asset | Current location | Lines |
|-------|-----------------|-------|
| `/codex` skill | `.claude/skills/codex/SKILL.md` | 247 |
| `codex-dialogue` agent | `.claude/agents/codex-dialogue.md` | 525 |
| Consultation contract | `docs/references/consultation-contract.md` | 395 |
| Profiles YAML | `docs/references/consultation-profiles.yaml` | — |

The Codex MCP server is external: `.mcp.json` wires Claude Code to `codex mcp-server` (Codex CLI, installed at `/Applications/Codex.app/...`). We control the config, not the binary.

---

## Design space explored

### Option A — Config + packaging (table stakes)

Bundle skill + agent + contract + profiles + `.mcp.json` config into one installable. Plugin's `.mcp.json` ships the `codex mcp-server` wiring so users don't manually configure it.

### Option B — Enforcement hooks (the real upgrade)

PreToolUse + PostToolUse hooks on `mcp__codex__codex` that code-enforce what the consultation contract currently only normatively specifies:

```
PreToolUse: mcp__codex__codex
  → run redaction check on outbound prompt (Python)
  → block if secrets detected
  → block if sandbox = danger-full-access
  → block if no consent context

PostToolUse: mcp__codex__codex
  → append consultation event to .codex-events.jsonl
```

### Option C — Profile UX

`/codex -p <profile>` flag parsing in the skill, resolving profile names to flag combos via profiles YAML.

### Option D — Event system (deferred)

Append-only consultation event log with KPI metrics + episodic index projections. Contingent on cross-model learning Phase 0.

---

## Converged architecture (from Codex consultation)

### Phasing

| Version | Content |
|---------|---------|
| v0.1 | Packaging + enforcement hooks (A + B together, with honest labeling) |
| v0.2 | Profile UX — `-p <profile>` flag parsing |
| v0.3 | Event system projections (contingent on learning Phase 0) |

Packaging and enforcement ship together in v0.1. Shipping packaging alone would mislabel the release — users would assume safety enforcement exists when it doesn't.

### Why not a wrapper MCP server

The wrapper MCP approach requires managing subprocess state for a stateful external binary (Codex maintains thread IDs and conversation history across calls). Proxying this cleanly requires keeping the subprocess alive and forwarding all state — non-trivial, and the failure modes (subprocess crash, state desync) are worse than hook failures.

Hooks are the correct enforcement mechanism for v0.1.

### Failure polarity (key framework from consultation)

| Mechanism | On failure (default) | v0.1 design |
|-----------|---------------------|-------------|
| PreToolUse hooks | Fail-open — crashes pass through by default (exit code semantics) | **Intentionally fail-closed** — errors explicitly converted to blocks |
| Wrapper MCP | Fail-closed by default | N/A (not v0.1) |

PreToolUse hooks are mechanically fail-open on crashes (only exit code 2 produces a block — unhandled exceptions exit with other codes and the call proceeds). The hook implementation must explicitly catch all errors and return a block decision. This is not the default — it must be designed in.

The choice between hooks and wrapper MCP is a threat model question, not an architecture preference:

- "Reduce accidental credential leaks" → hooks are proportionate (accidental-credential is the realistic threat for this system)
- "Zero tolerance; one leak is unacceptable" → wrapper required

**Decision:** Hooks are proportionate for v0.1, but must be explicitly designed as fail-closed.

### `updatedInput` decision

PreToolUse hooks CAN transform payloads via `updatedInput`. We're choosing not to use it for security enforcement. Reason: if multiple PreToolUse hooks write `updatedInput`, the merge behavior is undefined. In a security-critical path, undefined behavior is worse than a simpler guarantee.

**Decision: block-or-allow only for v0.1.** No in-flight redaction.

### v0.1 minimum viable controls

1. PreToolUse deny gate on `mcp__codex__codex`
2. Reuse `packages/context-injection/` redaction engine for detection logic — but patterns need tightening before hard-block use (see Hook detection architecture below)
3. Deny on secrets detected OR on hook errors — explicit error handling required (not the mechanical default; see Failure polarity)
4. Structured per-hook logging (each block logged with reason + timestamp)
5. Documented fail-open paths and limitations (user knows what the hook does and does not guarantee)
6. Defined escalation criteria to wrapper MCP (what would trigger the upgrade)

### Hook detection architecture (Q1 — evaluative consultation, 5 turns)

**Decision: Tiered detection — not full §7 parity, not minimal-only.**

The binary framing (full parity vs. minimal) was a false choice. The converged answer is three tiers:

| Tier | Behavior | Notes |
|------|---------|-------|
| Strict patterns | Hard-block | High-confidence matches only, tightened with word boundaries + mixed character classes + minimum length |
| Contextual patterns | Block with placeholder suppression | Suppress if meta-language nearby ("format", "example", "looks like") — downgrade from block to shadow |
| Broad patterns | Shadow-only | Append to telemetry, no blocking; promoted to strict/contextual via real-world block log data |

**`redact.py` patterns cannot be reused as-is.** `packages/context-injection/context_injection/redact.py` `_API_KEY_PREFIX_RE` (line ~89) matches discussion text like "sk-followed-by-40-characters." All patterns need tightening before hard-block use. Reuse the engine, not the regexes verbatim.

**Placeholder suppression** (emerged from dialogue): scan for meta-language words near a pattern match as a false-positive suppressor. Novel signal — neither side started with it.

**Contract scope settled:** §7 binds the skill and agent, not infrastructure. The hook is outside §7's scope. Starting with minimal/tiered detection is not a contract violation — no §7 amendment needed for detection scope choices. The contract's outcome-based invariant rewrite (see next section) is still required, but for a different reason.

**Pattern promotion path:** Broad → contextual → strict, gated by real-world FP data from the shadow tier.

### Install scope (Q2 — evaluative consultation, 5 turns)

**Decision: User-scope (`~/.claude/settings.json`) for v0.1 and beyond.**

**Four implementation guardrails:**

| # | Guardrail | Why |
|---|----------|-----|
| 1 | Remove `codex` entry from repo `.mcp.json` when plugin ships | Eliminates duplicate MCP definitions; prevents polluted dogfooding |
| 2 | Add MCP-availability guard to any nudge hook before including in plugin | Prevents "use Codex" nudges when Codex tools are unavailable |
| 3 | Gate nudge hook by explicit opt-in (env var or project marker) | User-scope hooks have global blast radius across all projects |
| 4 | Run clean-machine smoke tests (Codex CLI present and absent) before release | Validates graceful degradation |

**Key finding:** Hooks are dormant when their matched tool doesn't exist. If a user doesn't have Codex CLI installed, `mcp__codex__codex` never appears, so the PreToolUse hook never fires. This eliminates collaborator-disruption concerns that made project-scope seem risky.

**Hybrid approach (project plugin + local MCP config):** Technically viable — Claude Code composes MCP servers from all scopes into a unified tool namespace — but unnecessary given single-developer reality and the `tool-dev` marketplace's user-scope workflow.

**Implementation consequence:** The repo's existing `.mcp.json` `codex` entry must be migrated out when the plugin takes ownership. Otherwise there are two `codex` MCP registrations and dogfooding reflects hybrid state, not plugin-only state.

---

## Contract change required before v0.1 ships

**`docs/references/consultation-contract.md` §7 Safety Pipeline** currently mandates redaction:

> "Replace every detected candidate with `[REDACTED: credential material]`"

A hook that blocks instead of redacting is technically non-compliant with this. The invariant must be rewritten before enforcement hooks can ship:

**Current:** "Replace every detected candidate with `[REDACTED]`"
**Required:** "No credential-bearing payload is dispatched"

This framing makes both approaches (redact-and-continue, deny-and-block) contract-compliant without weakening the safety guarantee.

---

## Plugin structure (anticipated)

```
packages/plugins/codex/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── codex/
│       └── SKILL.md
├── agents/
│   └── codex-dialogue.md
├── hooks/
│   └── hooks.json          # PreToolUse + PostToolUse on mcp__codex__codex
├── scripts/
│   └── codex_guard.py      # Enforcement hook script (uses context-injection redaction engine)
├── references/
│   ├── consultation-contract.md
│   └── consultation-profiles.yaml
├── .mcp.json               # codex mcp-server wiring
├── README.md
└── CHANGELOG.md
```

---

## Wrapper MCP escalation (to define at v0.1 ship)

Must be documented at v0.1 ship time. Candidates (not yet decided):

- X% of blocks in 30 days (suggests threat is real, worth the wrapper complexity)
- Manual audit reveals a false negative that hooks would have caught
- Threat model changes from "accidental" to "adversarial" exfiltration

---

## Resolved decisions

| Question | Decision | Source |
|----------|---------|--------|
| Q1: Hook detection scope | Tiered detection (strict/contextual/shadow) — not full §7 parity, not minimal-only | Evaluative consultation, 5 turns |
| Q2: Install scope | User-scope with 4 guardrails | Evaluative consultation, 5 turns |

See Hook detection architecture and Install scope sections above for full reasoning.

---

## Deferrable (resolve during implementation)

- **Telemetry schema:** Exact shape of `.codex-events.jsonl` entries. Pre/post events and escalation triggers are the recommended shape — no concrete schema yet.
- **Escalation criteria thresholds:** Specific numeric thresholds for upgrading to wrapper MCP (e.g., block rate %, false negative discovery process).
- **FP corpus definition:** What constitutes sufficient real-world data for promoting a pattern from shadow to hard-block tier.
- **De-correlation strategy:** How to ensure hook-level detection and prompt-level safety (§7) fail independently rather than on the same inputs. Implementation detail — relevant when tuning the shadow tier.
- **Nudge hook availability-check mechanism:** Exact runtime check for MCP tool presence before emitting a nudge. Required by guardrail 2.
- **MCP scope precedence for plugin-bundled servers:** Whether Claude Code's local > project > user precedence applies identically to plugin-bundled MCP servers vs. `claude mcp add` servers. Verify during implementation.
