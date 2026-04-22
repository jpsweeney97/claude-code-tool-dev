# T-07 Slice 7c: Cross-Model → Codex-Collaboration Migration and Parity

## Overview

| Attribute | Value |
|-----------|-------|
| Artifact | This document |
| Type | Migration documentation + parity verification |
| Code changes | None — doc-only |
| Branch | `feature/t07-migration-7c` |
| ACs addressed | "Migration docs show how to replace each cross-model workflow" + "A parity matrix exists and covers consult, dialogue, delegate, analytics, and review" |
| Closeout | After merge, update T-07 ticket ACs citing this artifact. This document is the evidence; ticket checkbox update is a separate step. |

This document maps every cross-model surface to its codex-collaboration
replacement, verifies workflow parity across the five required workflows,
and provides a command-level migration guide.

**This document does NOT authorize removal.** Context-injection removal is
7d. Cross-model removal is 7e. Removal gates (live `/delegate` smoke,
parity checklist execution) are defined in 7e.

---

## 1. Workflow Parity Matrix

The five workflows required by the T-07 AC:

| # | Workflow | Cross-model surface | Codex-collaboration replacement | Parity status | Delivery | Evidence |
|---|----------|--------------------|---------------------------------|---------------|----------|----------|
| 1 | **Consult** | `/codex` skill → `codex_shim.py` MCP → `codex_consult.py` adapter → `codex exec` | `consult-codex` skill → `codex.consult` MCP tool → `control_plane.py` → App Server JSON-RPC | Functional replacement; user-facing flags dropped, profile-based config instead (see §3a) | T-02 | `skills/consult-codex/SKILL.md` |
| 2 | **Dialogue** | `/dialogue` skill → gatherer agents → `codex-dialogue` agent → context-injection MCP | `dialogue` skill → gatherer agents → `dialogue-orchestrator` agent → server-side dialogue tools | Functional replacement with scouting model change (see §3b) | T-04 | `skills/dialogue/SKILL.md`, `agents/dialogue-orchestrator.md` |
| 3 | **Delegate** | `/delegate` skill → `codex_delegate.py` 14-step pipeline → `codex exec` | `delegate` skill → `codex.delegate.start` MCP tool → delegation controller → App Server + worktree isolation | Functional replacement with lifecycle change (see §3c) | T-06 | `skills/delegate/SKILL.md`, `server/delegation_controller.py` |
| 4 | **Analytics** | `/consultation-stats` skill → `compute_stats.py` → `~/.claude/.codex-events.jsonl` | `codex-analytics` skill → `analytics/outcomes.jsonl` + `audit/events.jsonl` | Functional replacement with different data model (see §3d) | T-07/7a | `skills/codex-analytics/SKILL.md`, PR #116 |
| 5 | **Review** | `codex-reviewer` agent (direct invocation, fail-soft analytics via `emit_analytics.py`) | `codex-review` skill → `codex.consult` with `workflow="review"` | Functional replacement; elevated from agent to skill, analytics model changed (see §3e) | T-07/7b | `skills/codex-review/SKILL.md`, PR #117 |

**Verdict:** All five workflows have delivered replacements. No workflow
remains without a codex-collaboration equivalent.

---

## 2. Removal Inventory

Every cross-model surface, its replacement status, and whether the source
is still present. This section prevents 7c from being read as a deletion
authorization.

### 2a. Skills

| Cross-model skill | Replacement | Replacement status | Source status | Removal owner |
|---|---|---|---|---|
| `skills/codex/SKILL.md` | `consult-codex` skill | Delivered (T-02) | Present | 7e |
| `skills/dialogue/SKILL.md` | `dialogue` skill | Delivered (T-04) | Present | 7e |
| `skills/delegate/SKILL.md` | `delegate` skill | Delivered (T-06) | Present | 7e |
| `skills/consultation-stats/SKILL.md` | `codex-analytics` skill | Delivered (T-07/7a) | Present | 7e |

### 2b. Agents

| Cross-model agent | Replacement | Replacement status | Source status | Removal owner |
|---|---|---|---|---|
| `agents/codex-dialogue.md` | `agents/dialogue-orchestrator.md` | Delivered (T-04) | Present | 7e |
| `agents/codex-reviewer.md` | `codex-review` skill | Delivered (T-07/7b) | Present | 7e |
| `agents/context-gatherer-code.md` | `agents/context-gatherer-code.md` (carried forward) | Delivered (T-04) | Present in both plugins | 7e (cross-model copy) |
| `agents/context-gatherer-falsifier.md` | `agents/context-gatherer-falsifier.md` (carried forward) | Delivered (T-04) | Present in both plugins | 7e (cross-model copy) |

### 2c. Hooks

| Cross-model hook | Event | Replacement | Replacement status | Source status | Removal owner |
|---|---|---|---|---|---|
| `codex_guard.py` (PreToolUse) | Credential scan on `codex`/`codex-reply` | `codex_guard.py` (PreToolUse) in codex-collaboration, scans `codex.consult`/`codex.dialogue.*` | Delivered (T-03) | Present in both plugins | 7e (cross-model copy) |
| `codex_guard.py` (PostToolUse) | Event logging on `codex`/`codex-reply` | Server-side outcome recording in `control_plane.py` | Delivered (T-03; extended by T-07/7a) | Present | 7e |
| `nudge_codex.py` (PostToolUseFailure) | Bash failure nudge → suggest `/codex` | No port planned | N/A — dropped by reconciliation | Present | 7e |

### 2d. MCP Servers

| Cross-model MCP server | Tools | Replacement | Replacement status | Source status | Removal owner |
|---|---|---|---|---|---|
| `codex_shim.py` (Codex) | `codex`, `codex-reply` | codex-collaboration MCP server (`server/mcp_server.py`) with `codex.consult`, `codex.status`, `codex.dialogue.*`, `codex.delegate.*` | Delivered (T-02) | Present | 7e |
| `context-injection/` (Context Injection) | `process_turn`, `execute_scout` | Retired — Claude-side scouting replaces mid-conversation evidence gathering (T-04 retirement decision) | Adjudication complete | Present | **7d** |

### 2e. Shared Scripts (complete inventory)

All 17 Python scripts in `cross-model/scripts/`:

| Group | Cross-model script | Codex-collaboration equivalent | Disposition |
|---|---|---|---|
| **Safety** | `credential_scan.py` | `server/credential_scan.py` (rewritten) | Replaced |
| | `secret_taxonomy.py` | `server/secret_taxonomy.py` (carried forward) | Replaced |
| | `consultation_safety.py` | `server/consultation_safety.py` (rewritten) | Replaced |
| | `codex_guard.py` | `scripts/codex_guard.py` (rewritten for new MCP tool names) | Replaced |
| **Transport/Adapters** | `codex_consult.py` | `server/control_plane.py` + `server/codex_compat.py` | Replaced (rewritten as server architecture) |
| | `codex_delegate.py` | `server/delegation_controller.py` + `server/worktree_manager.py` | Replaced (rewritten as server architecture) |
| | `codex_shim.py` | `server/mcp_server.py` (stdio MCP server, not a FastMCP shim) | Replaced (rewritten) |
| **Analytics pipeline** | `emit_analytics.py` | Server-side outcome recording in `control_plane.py` + `server/journal.py` | Replaced (rewritten as structured journaling) |
| | `event_log.py` | `server/journal.py` (POSIX atomic append) | Replaced |
| | `event_schema.py` | `server/models.py` (Pydantic models) | Replaced (rewritten as typed models) |
| | `read_events.py` | Analytics script reads `outcomes.jsonl`/`events.jsonl` directly | Replaced |
| | `compute_stats.py` | `codex-analytics` skill + inline analytics script | Replaced (T-07/7a) |
| | `stats_common.py` | Inlined into analytics script | Replaced |
| **Learning retrieval** | `retrieve_learnings.py` | `server/retrieve_learnings.py` (carried forward) | Replaced |
| **Validation** | `validate_profiles.py` | `server/profiles.py` (runtime validation) | Replaced |
| | `validate_graduation.py` | No direct equivalent (graduation validation is a dev-time script) | Dropped (dev tooling) |
| **Nudge** | `nudge_codex.py` | No port planned | Dropped (leaf, opt-in, low usage) |

**Inventory completeness:** 17/17 scripts accounted for. 15 replaced
(rewritten in server architecture or carried forward), 2 dropped.

### 2f. References and Configuration

| Cross-model artifact | Codex-collaboration equivalent | Disposition |
|---|---|---|
| `references/consultation-contract.md` | Codex-collaboration operates under its own contract (server-enforced, not Claude-cognitive) | Superseded |
| `references/context-injection-contract.md` | Retired with context-injection (T-04) | Superseded |
| `references/composition-contract.md` | Hosted in cross-model as authoring origin; no local consumers | Superseded (no port needed) |
| `references/dialogue-synthesis-format.md` | Dialogue-orchestrator agent defines its own output format | Superseded |
| `references/contract-agent-extract.md` | Agent-readable extract; no equivalent needed (server enforces) | Superseded |
| `references/consultation-profiles.yaml` | `references/consultation-profiles.yaml` in codex-collaboration | Carried forward |
| `.mcp.json` | `.mcp.json` in codex-collaboration (different server registration) | Replaced |
| `.claude-plugin/plugin.json` | `.claude-plugin/` in codex-collaboration | Replaced |
| `README.md` | To be written for codex-collaboration (not yet updated) | **Gap** — does not block 7c |
| `HANDBOOK.md` | To be written for codex-collaboration | **Gap** — does not block 7c |
| `CHANGELOG.md` | To be written for codex-collaboration | **Gap** — does not block 7c |

### 2g. Package Metadata

| Cross-model artifact | Codex-collaboration equivalent | Disposition |
|---|---|---|
| `pyproject.toml` | `pyproject.toml` in codex-collaboration | Independent package |
| `context-injection/pyproject.toml` | Retired with context-injection | 7d removal |
| `context-injection/` (entire package) | Retired — T-04 decision | **7d removal** |
| `tests/` | `tests/` in codex-collaboration (current test suite) | Independent test suite |
| `testdata/` | No equivalent (credential parity corpus) | Dropped with cross-model |

---

## 3. Migration Guide by Workflow

### 3a. Consult: `/codex` → `/consult-codex`

| Aspect | Cross-model (`/codex`) | Codex-collaboration (`/consult-codex`) |
|---|---|---|
| Command | `/codex PROMPT` | `/consult-codex PROMPT` |
| Flags | `-m` (model), `-s` (sandbox), `-a` (approval), `-t` (effort) | None — server selects defaults from profile |
| Profile support | Via flags only | Via `codex.consult` `profile` parameter |
| Credential scanning | `codex_guard.py` PreToolUse hook | `codex_guard.py` PreToolUse hook + server-side `consultation_safety.py` |
| Analytics | `emit_analytics.py` → `~/.claude/.codex-events.jsonl` | Server-side → `analytics/outcomes.jsonl` |
| Transport | `codex_shim.py` FastMCP → `codex_consult.py` adapter → `codex exec` subprocess | `codex.consult` MCP tool → `control_plane.py` → `runtime.py` App Server JSON-RPC |
| Thread continuation | `codex-reply` with `threadId` | Not exposed at skill level (server manages threads) |

**Migration notes:**
- No user-facing flags on `consult-codex`. Profile-based configuration
  replaces per-call flag overrides.
- Thread continuation is not exposed at the skill level. Multi-turn
  conversations should use `/dialogue` instead.

### 3b. Dialogue: `/dialogue` → `/dialogue`

| Aspect | Cross-model (`/dialogue`) | Codex-collaboration (`/dialogue`) |
|---|---|---|
| Command | `/dialogue "question" [-p posture] [-n turns] [--profile name] [--plan]` | `/dialogue "question" [-p posture] [-n turns]` |
| Flags | `-p`, `-n`, `--profile`, `--plan` | `-p`, `-n` |
| `--profile` flag | Supported — selects named preset | Not exposed as a flag (profile selection is server-side) |
| `--plan` flag | Supported — question decomposition before dialogue | Not exposed (planning is not ported) |
| Scouting model | Context-injection MCP server (HMAC-validated, stateful, per-turn via `process_turn`/`execute_scout`) | Claude-side host-tool scouting: pre-dialogue gatherers + Phase 1 bounded inline scouting + Phase 3 per-turn verification scouting |
| Agents | `codex-dialogue` + 2 gatherers | `dialogue-orchestrator` + 2 gatherers |
| Context injection MCP | `process_turn` + `execute_scout` MCP tools (stateful per-process) | Retired — scouting reimplemented as Claude-side Read/Grep/Glob calls |
| Analytics | `emit_analytics.py` → `~/.claude/.codex-events.jsonl` | Server-side → `analytics/outcomes.jsonl` |

**Migration notes:**
- `--profile` and `--plan` flags are not ported to codex-collaboration's
  `/dialogue`. Profile selection happens at the server level via
  `codex.dialogue.start` parameters.
- The scouting model changed architecturally. Cross-model uses a
  stateful context-injection MCP server with HMAC-validated per-turn
  scouting (`process_turn` → `execute_scout`). Codex-collaboration
  retires the context-injection MCP server (T-04 decision) but
  reimplements scouting as Claude-side host-tool calls in three phases:
  (1) pre-dialogue gatherer agents, (2) Phase 1 bounded inline scouting
  (at most 5 Read/Grep/Glob calls, `dialogue-orchestrator.md` Phase 1),
  (3) Phase 3 per-turn verification scouting within the dialogue loop
  (`dialogue-orchestrator.md` Phase 3, Step 5). The mechanism losses from
  retiring the MCP server (L1 scout integrity, L2 plateau/budget control,
  L3 per-scout redaction) are accepted trade-offs; the scouting
  *capability* is preserved via different architecture.
- The `codex-dialogue` agent is replaced by `dialogue-orchestrator`.
  Both agents use the same gatherer agents (`context-gatherer-code`,
  `context-gatherer-falsifier`).

### 3c. Delegate: `/delegate` → `/delegate`

| Aspect | Cross-model (`/delegate`) | Codex-collaboration (`/delegate`) |
|---|---|---|
| Command | `/delegate [-m] [-s] [-t] [--full-auto] PROMPT` | `/delegate "objective" \| start \| poll \| approve \| deny \| promote \| discard` |
| Flags | `-m`, `-s`, `-t`, `--full-auto` | None — lifecycle subcommands instead |
| Lifecycle | Single invocation → 14-step pipeline → review | Multi-step: `start` → `poll` → escalation handling → `promote`/`discard` |
| Isolation | In-place (requires clean git tree) | Worktree-based isolation (`server/worktree_manager.py`) |
| Review gate | Claude reviews all changes after completion | Claude reviews before `promote` (explicit promotion step) |
| Sandbox | `-s read-only` or `-s workspace-write` | Server-managed sandbox via execution runtime |
| Analytics | `emit_analytics.py` → `~/.claude/.codex-events.jsonl` | Server-side → `analytics/outcomes.jsonl` + `DelegationOutcomeRecord` |

**Migration notes:**
- The delegation model changed from a single-invocation pipeline to an
  interactive lifecycle with explicit `start`/`poll`/`promote`/`discard`
  steps. This gives the user more control but requires multiple
  interactions.
- Worktree isolation replaces the clean-tree gate for *starting*
  delegation. However, `promote` still has primary-workspace prechecks:
  HEAD must match `base_commit`, worktree must be clean, index must be
  clean, and regenerated artifact hash must match the reviewed hash
  (`delegation_controller.py:947-963`). A dirty primary workspace will
  fail at promotion, not at start.
- `--full-auto` is not ported. The interactive lifecycle is the
  default and only mode.

### 3d. Analytics: `/consultation-stats` → `/codex-analytics`

| Aspect | Cross-model (`/consultation-stats`) | Codex-collaboration (`/codex-analytics`) |
|---|---|---|
| Command | `/consultation-stats [--period days] [--type filter]` | `/codex-analytics` |
| Flags | `--period` (7/30/0), `--type` (all/consultation/dialogue/delegation/security) | None — skill computes all views |
| Data source | `~/.claude/.codex-events.jsonl` (flat event log) | `analytics/outcomes.jsonl` + `audit/events.jsonl` (typed streams) |
| Views | Usage, dialogue, context, security, delegation | Usage, reliability/security, context/runtime, delegation, review |
| Review view | Fail-soft flat events via `emit_analytics.py` (`consultation_source: "reviewer"`) | First-class `workflow="review"` consult outcomes in `outcomes.jsonl` |

**Migration notes:**
- The data model changed from a single flat event log to two typed
  streams (`outcomes.jsonl` for results, `events.jsonl` for audit trail).
- Review analytics changed from fail-soft flat events (cross-model's
  `codex-reviewer` emits `consultation_outcome` with
  `consultation_source: "reviewer"` via `emit_analytics.py`) to
  first-class `workflow="review"` consult outcomes in codex-collaboration.
  The data model is different, but both systems produce analytics for
  review invocations.
- Known limitation (7a): credential blocks/shadows and promotion
  rejections are surfaced as `unavailable (not emitted to audit stream)`.

### 3e. Review: `codex-reviewer` agent → `/codex-review`

| Aspect | Cross-model (`codex-reviewer`) | Codex-collaboration (`/codex-review`) |
|---|---|---|
| Invocation | Direct agent invocation (not a slash command) | `/codex-review [branch \| commit-range \| 'staged' \| 'unstaged']` |
| Type | Agent (211 lines) | Skill (270 lines) |
| Turns | 2-turn max Codex consultation | Configurable via profile (`code-review`: 4 turns, `deep-review`: 8 turns) |
| Diff handling | 3-tier: full ≤500, summarize 501-1500, reject >1500 | Same thresholds |
| Analytics | Fail-soft `consultation_outcome` with `consultation_source: "reviewer"` via `emit_analytics.py` | First-class `workflow="review"` consult outcome in `outcomes.jsonl` |
| Synthesis | 5-step agent process | 9-step skill procedure with byte-budgeted objective |

**Migration notes:**
- Elevated from agent to user-invocable skill. Users invoke it as
  `/codex-review` instead of triggering the agent directly.
- Analytics model changed: cross-model emits fail-soft flat
  `consultation_outcome` events with `consultation_source: "reviewer"`;
  codex-collaboration records review invocations as first-class
  `workflow="review"` consult outcomes with full outcome metadata.
- The byte budget (20KB hard, 16KB soft) is new — cross-model's agent
  had no explicit budget for the review payload.

---

## 4. Infrastructure Migration

### 4a. Hook Mapping

| Event | Cross-model | Codex-collaboration | Notes |
|---|---|---|---|
| PreToolUse (credential scan) | `codex_guard.py` on `codex`/`codex-reply` | `codex_guard.py` on `codex.consult`/`codex.dialogue.*` | Rewritten for new MCP tool names |
| PostToolUse (telemetry) | `codex_guard.py` on `codex`/`codex-reply` | Server-side recording (no PostToolUse hook) | Telemetry moved into server |
| PostToolUseFailure (nudge) | `nudge_codex.py` on Bash | Not ported | Dropped (leaf, opt-in) |
| SessionStart | None | `publish_session_id.py` | New in codex-collaboration |
| SubagentStart/Stop | None | `containment_lifecycle.py` on `shakedown-dialogue`/`dialogue-orchestrator` | New in codex-collaboration |
| PreToolUse (containment) | None | `containment_guard.py` on `Read`/`Grep`/`Glob` | New in codex-collaboration |

### 4b. MCP Server Architecture

| Aspect | Cross-model | Codex-collaboration |
|---|---|---|
| Server type | FastMCP shim (`codex_shim.py`, 122 lines) | stdio MCP server (`mcp_server.py`) |
| Transport | Shim → `codex_consult.py` adapter → `codex exec` subprocess | Server → `control_plane.py` → `runtime.py` (`AppServerRuntimeSession`) → `codex app-server` JSON-RPC |
| Tools | 2 (`codex`, `codex-reply`) | 8+ (`codex.status`, `codex.consult`, `codex.dialogue.*`, `codex.delegate.*`) |
| State | Stateless (thread state in Codex service) | Stateful (turn store, job store, lineage store, journal) |
| Context injection | Separate MCP server (`context-injection/`) | None (retired) |

---

## 5. Deferred to 7d/7e

### 7d: Context-Injection Removal

- Remove `packages/plugins/cross-model/context-injection/` (entire package)
- Removal gate: T-04 retirement decision (demonstrated-not-scored)
- Caveats that travel with removal:
  - `T-20260416-01` (reply-path extraction mismatch) remains open
  - Mechanism losses L1/L2/L3 acknowledged
  - Capture sequence spans multiple doc commits

### 7e: Cross-Model Removal + Verification

- Remove `packages/plugins/cross-model/` (entire package)
- **Pre-removal gates:**
  - This parity matrix verified (7c — this document)
  - Context-injection removed (7d)
  - Live `/delegate` smoke passed (or explicit App Server deferral
    recorded with same transparency as T-06's deferral)
- Post-removal verification:
  - No cross-model imports remain in the repo
  - Codex-collaboration tests still pass
  - All five workflows functional via codex-collaboration

**Note:** This parity matrix (7c) is an *input* to 7e's verification
checklist, not the completed verification itself. 7e must execute the
parity checklist against live state at removal time.

---

## 6. References

| Resource | Location | Role |
|----------|----------|------|
| T-07 ticket | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` | AC definitions |
| T-07 reconciliation | Same file, "Design Reconciliation" section | Draft parity matrix, slice boundaries |
| T-04 retirement decision | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Context-injection adjudication |
| T-06 delegate evidence | `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md` | Delegation lifecycle |
| Capability analysis | `docs/reviews/2026-03-17-cross-model-capability-analysis.md` | Cross-model surface inventory |
| Cross-model README | `packages/plugins/cross-model/README.md` | Surface documentation (note: describes cross-model, not codex-collaboration) |
| PR #116 (7a) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/116 | Analytics + workflow plumbing |
| PR #117 (7b) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/117 | codex-review skill |
