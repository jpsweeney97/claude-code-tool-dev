# M9 Skill Layer Design

Connect the ticket engine (classify → plan → preflight → execute pipeline) to Claude Code's skill system.

## Status

Designed. Not yet implemented.

**Supersedes:** Skill layer sections of `2026-03-02-ticket-plugin-design.md` and `2026-03-03-ticket-plugin-phase2-design.md`. Decisions validated via Codex dialogue (thread `019cbc75-3ce7-72b1-9f56-e134af8185c3`, 6 turns, collaborative posture, 9 resolved / 2 unresolved / 3 emerged).

## Artifacts

### Skills

| Skill | Path | Invocation | Auto-invoke |
|-------|------|------------|-------------|
| `/ticket` | `skills/ticket/SKILL.md` | Manual (`disable-model-invocation: true`) | No |
| `/ticket-triage` | `skills/ticket-triage/SKILL.md` | Manual + auto | Yes |

### Infrastructure Changes

| Change | File | Purpose |
|--------|------|---------|
| Add `__main__` CLI block | `scripts/ticket_read.py` | Enable Bash invocation for list/query |
| Add `__main__` CLI block | `scripts/ticket_triage.py` | Enable Bash invocation for dashboard/audit |
| Add allowlist branches | `hooks/ticket_engine_guard.py` | Allow read/triage through hook |
| Version bump 1.0.0 → 1.1.0 | `.claude-plugin/plugin.json` | Release marker |

### Not Built

No context-gathering subagent. The engine's `need_fields` and preflight gating handle field collection. A subagent adds orchestration complexity without proportionate value, and the subagent nesting constraint (`subagents cannot spawn other subagents`) is a hard blocker for future composition.

## Architecture

### Execution Model

Fully inline. Claude runs in the main conversation context with full conversation history. The 4-stage pipeline runs as sequential Bash calls via the user entrypoint. Read-only operations bypass the engine pipeline and call `ticket_read.py` or `ticket_triage.py` directly.

### Why No Subagent

The Codex dialogue evaluated the subagent approach and rejected it:

1. **Hook guard conflict:** A subagent calling `ticket_engine_user.py` triggers `hook_request_origin="agent"`, causing `origin_mismatch` rejection. Solving this requires either modifying the hook guard (weakens security boundary) or a delegation token (adds bypass mechanism).
2. **Nesting constraint:** Subagents cannot spawn other subagents. A context-gathering subagent cannot invoke the engine — the parent must do it anyway.
3. **Proportionality:** The 4 pipeline CLI calls produce compact JSON. The "noise" is manageable — less chatty than the context gathering a subagent would replace.

### Why `disable-model-invocation: true` on `/ticket`

The mutation skill writes files and creates audit trail entries. The existing design deliberately rejected auto-invocation for mutation skills as unsafe. The ops/triage split exists precisely because:

- `/ticket-triage` is safe to auto-invoke (read-only, no mutations)
- `/ticket` requires explicit user intent (mutations, side effects)

The autonomy model gates agent mutations independently at preflight/execute, but skill-level `disable-model-invocation` prevents Claude from even loading the mutation instructions without user intent.

## `/ticket` Skill

### Frontmatter

```yaml
name: ticket
description: "Manage codebase tickets (create, update, close, reopen, query, list). This skill should be used when the user says \"create a ticket\", \"update ticket T-...\", \"close ticket\", \"reopen ticket\", \"list tickets\", \"show open tickets\", \"find ticket about...\", or asks to track a bug, feature, or work item as a ticket."
disable-model-invocation: true
argument-hint: "[create|update|close|reopen|list|query] [ticket-id or details]"
allowed-tools:
  - Bash
  - Write
  - Read
```

### Routing

First-token dispatch from `$ARGUMENTS` or natural language intent:

| First Token / Intent | Action | Execution Path |
|---------------------|--------|----------------|
| `create` / "track this bug" | Create | Engine pipeline (classify → plan → preflight → execute) |
| `update` / "change priority of T-..." | Update | Engine pipeline |
| `close` / "mark T-... as done" | Close | Engine pipeline |
| `reopen` / "reopen T-..." | Reopen | Engine pipeline (user-only in v1.0) |
| `list` / "show open tickets" | List | `ticket_read.py list` (direct) |
| `query` / "find ticket about auth" | Query | `ticket_read.py query` (direct) |

### Mutation Flow (Create)

```
User: /ticket create Fix the auth token race condition
  ↓
1. Extract details from conversation context
   (title, problem, priority, key files, tags)
  ↓
2. Present confirmation summary:
   "I'll create a ticket with:
    Title: Fix auth token race condition
    Priority: high
    Problem: [extracted from discussion]
    Key files: src/auth.py
    Continue? [y/edit/n]"
  ↓
3. On confirmation: write payload JSON to temp file
  ↓
4. Run pipeline (4 sequential Bash calls):
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py classify /tmp/payload.json
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py plan /tmp/payload.json
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py preflight /tmp/payload.json
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py execute /tmp/payload.json
  ↓
5. Handle response states:
   ok_create        → report success (ticket ID + path)
   need_fields      → ask user for missing fields, re-run from plan
   duplicate_candidate → show match, ask for dedup_override
   policy_blocked   → report error with guidance
   escalate         → report error with guidance
```

### Confirmation Gate

All mutations show a proposed-fields preview and ask for user confirmation before calling `execute`. This is a skill-level UX gate — no engine state needed.

- If user confirms → proceed to pipeline
- If user edits fields → update payload, re-run from `plan` → `preflight`
- If user cancels → stop

For `update`, `close`, and `reopen`: the confirmation shows the current ticket state alongside the proposed changes.

### Progressive Disclosure

- `SKILL.md` (~250 lines): routing table, confirmation UX, pipeline mechanics, response state handling
- `references/pipeline-guide.md`: per-operation payload schemas, field defaults, detailed examples, edge cases

## `/ticket-triage` Skill

### Frontmatter

```yaml
name: ticket-triage
description: "Analyze ticket health, detect stale tickets, blocked dependency chains, and audit activity. This skill should be used when the user says \"triage tickets\", \"what's in the backlog\", \"show ticket health\", \"any stale tickets\", \"ticket dashboard\", or at session start for project orientation."
allowed-tools:
  - Bash
  - Read
```

No `disable-model-invocation` — proactive, auto-invocable. Read-only, no mutation risk.

### Procedure

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_triage.py dashboard <tickets_dir>`
2. Parse JSON output (counts, stale, blocked_chains, size_warnings)
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_triage.py audit <tickets_dir>`
4. Present formatted report
5. Add opinionated analysis: suggest priority changes, identify closable tickets, recommend unblocking steps

### Scope

The script provides data; the skill provides judgment. This extends beyond raw triage output with actionable recommendations.

Size: ~80 lines. No supporting reference files needed.

## Infrastructure Changes

### `ticket_read.py` CLI Block

Add `__main__` dispatch:

| Subcommand | Arguments | Wraps |
|-----------|-----------|-------|
| `list` | `--status`, `--priority`, `--tag`, `--include-closed`, `<tickets_dir>` | `list_tickets`, `filter_tickets` |
| `query` | `<search_term>`, `--fuzzy`, `<tickets_dir>` | `fuzzy_match_id`, `filter_tickets` |

Output: JSON to stdout. Envelope: `{"state": "ok", "data": {...}}`.
Exit codes: 0 (success), 1 (error).

### `ticket_triage.py` CLI Block

Add `__main__` dispatch:

| Subcommand | Arguments | Wraps |
|-----------|-----------|-------|
| `dashboard` | `--tickets-dir <path>` | `triage_dashboard` |
| `audit` | `--tickets-dir <path>`, `--days N` | `triage_audit_report` |

Output: JSON to stdout. Same envelope pattern.
Exit codes: 0 (success), 1 (error).

No wrapper script (e.g., `ticket_triage_user.py`) — CLI added directly to existing module.

### Guard Hook Allowlist Expansion

Expand from 2 branches to 4 using execution-shape matching (not substring matching):

| Branch | Pattern | Trust Injection |
|--------|---------|-----------------|
| Engine (user) | `python3 ${PLUGIN_ROOT}/scripts/ticket_engine_user.py <subcommand> <path>` | Full (session_id, hook_injected, hook_request_origin) |
| Engine (agent) | `python3 ${PLUGIN_ROOT}/scripts/ticket_engine_agent.py <subcommand> <path>` | Full |
| Read | `python3 ${PLUGIN_ROOT}/scripts/ticket_read.py <subcommand> [args]` | None (read-only) |
| Triage | `python3 ${PLUGIN_ROOT}/scripts/ticket_triage.py <subcommand> [args]` | None (read-only) |

Execution-shape matching prevents blocking benign commands like `cat ticket_triage.py` or `rg ticket_read`. The hook checks the full command structure against allowlist regexes anchored to `${CLAUDE_PLUGIN_ROOT}`.

Read/triage branches pass through without trust injection — they're read-only with no autonomy policy.

### Plugin Manifest

Version bump `.claude-plugin/plugin.json` from 1.0.0 → 1.1.0. No explicit `skills` field needed — Claude Code auto-discovers `skills/` directories.

## Decisions

### Keep `disable-model-invocation: true` on mutation skill

**Driver:** Existing design deliberately rejected auto-invocation for mutation skills. Convergence in Codex dialogue — both sides agreed independently.

**Rejected:** Auto-invocation gated by autonomy model alone. The autonomy model is a separate defense layer; skill-level invocation control is the first gate.

### Include `ticket-triage` in M9 (not Phase 3)

**Driver:** Triage script already exists from M8. Skill wrapping is trivial. Without triage there's no NL gateway for ticket discoverability. Codex conceded after one turn.

**Guardrails:** Bash-only tools, deterministic script calls, no mutation paths.

### Name the skill `ticket` (not `ticket-ops`)

**Driver:** Safety comes from behavior (`disable-model-invocation`, tool permissions, guard hook), not from display name. `/ticket` is the natural UX. Codex conceded.

**Note:** Internal docs retain "ticket-ops" as the architectural role label where the ops/triage distinction matters.

### No context-gathering subagent

**Driver:** Engine already handles `need_fields` and preflight gating. Subagent nesting constraint is a hard blocker. Adding orchestration complexity is unjustified. Convergence in dialogue.

### Route query/list through `ticket_read.py` directly

**Driver:** Read operations don't need the engine pipeline (classify/plan/preflight/execute). Direct script calls are simpler and faster. The engine pipeline is for mutations.

### Guard hook uses execution-shape matching

**Driver:** Substring matching (`"ticket_engine" in command`) blocks benign commands (e.g., `cat`, `rg`, `wc -l`) when file paths contain `ticket_engine`. Execution-shape matching checks the full command structure against anchored regexes. Emerged from dialogue.

### Clean create confirmation is skill-level UX

**Driver:** No engine state needed. The skill presents a preview and waits for user confirmation before calling `execute`. If user edits fields, re-run from `plan`. Convergence in dialogue.

## Unresolved (Runtime-Testable)

These are not architectural blockers. Test at M9 gate:

1. **Plugin skill namespacing:** Is the invocation `/ticket` or `/ticket:ticket`? Test in a live session.
2. **Scoped `allowed-tools` syntax:** Does `Bash(ticket_engine_user.py)` work in plugin skill runtime? Treat as optional defense-in-depth; guard hook is primary enforcement.

## M9 Gate Checklist

| # | Check | Method |
|---|-------|--------|
| 1 | `/ticket create` works in live session | Manual — create ticket from conversation context |
| 2 | `/ticket list` works | Manual — list and filter tickets |
| 3 | `/ticket update` works | Manual — change priority/status |
| 4 | `/ticket close` works | Manual — close with archive |
| 5 | `/ticket reopen` works | Manual — reopen a closed ticket |
| 6 | `/ticket-triage` works | Manual — run triage dashboard |
| 7 | `/ticket-triage` auto-invokes | Test with "any stale tickets?" |
| 8 | Guard hook allows read/triage | Verify pass-through |
| 9 | Guard hook blocks unknown scripts | Verify denial |
| 10 | `need_fields` loop works | Create with missing fields |
| 11 | `duplicate_candidate` loop works | Create duplicate ticket |
| 12 | Confirmation gate works | Verify preview before execute |
| 13 | Plugin skill namespacing resolved | Test `/ticket` vs `/ticket:ticket` |
| 14 | All existing tests pass | `cd packages/plugins/ticket && uv run pytest` (318+) |
| 15 | New tests for CLI blocks | `ticket_read.py` and `ticket_triage.py` `__main__` |
| 16 | New tests for guard hook branches | Read/triage allowlist patterns |
| 17 | Ruff clean | `uv run ruff check packages/plugins/ticket` |
| 18 | Version bump | `plugin.json` at 1.1.0 |

## References

| Resource | Location |
|----------|----------|
| Ticket contract | `references/ticket-contract.md` |
| Original design | `docs/plans/2026-03-02-ticket-plugin-design.md` |
| Phase 2 design | `docs/plans/2026-03-03-ticket-plugin-phase2-design.md` |
| Skills guide | `docs/references/skills-guide.md` |
| Codex dialogue thread | `019cbc75-3ce7-72b1-9f56-e134af8185c3` |
