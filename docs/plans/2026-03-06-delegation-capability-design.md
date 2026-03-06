# Delegation Capability — Design Spec

**Date:** 2026-03-06
**Status:** Design — pending review
**Source:** Comparison with [skill-codex](https://github.com/skills-directory/skill-codex.git) + 2 Codex consultations

---

## Problem

The cross-model plugin treats Codex exclusively as an **advisor** (text-in/text-out consultation via MCP). It cannot delegate execution tasks — have Codex read files, run commands, write code, and produce diffs. This is a fundamentally different interaction pattern (worker vs. peer) that the plugin currently lacks.

The `skill-codex` project solves this with a 65-line skill that shells out to `codex exec`. That approach works but has no credential protection, no analytics, no diff review, and no dirty-tree safety. This spec designs a delegation capability that integrates with the existing plugin infrastructure.

## Prior Art: skill-codex

| Dimension | skill-codex | cross-model (current) |
|-----------|-------------|----------------------|
| Integration | Bash → `codex exec` | MCP server (`codex mcp-server`) |
| Codex role | Worker (executes tasks) | Advisor (gives opinions) |
| Credential protection | None | Tiered hook guard (strict/contextual/broad) |
| Analytics | None | Event log + consultation stats |
| Diff review | None | N/A (no file changes) |
| Multi-turn | `codex exec resume --last` | Full dialogue pipeline with convergence |

The two patterns are complementary. Delegation fills a gap that consultation deliberately doesn't address.

---

## Architecture

### New verb, not an extension of `/codex`

Delegation gets a separate `/delegate` skill. Reasons:

1. `/codex` is hardwired to `consultation_outcome` events and `mode="server_assisted"` throughout the skill, analytics emitter, and event reader.
2. The consultation contract frames Codex as a consultant, not an executor. Adding `--exec` would overload the verb and muddy the safety model.
3. Separate verb = separate contract, separate analytics, separate safety invariants.

### Adapter script, not raw shell construction

The skill does not construct `codex exec` commands inline. A local adapter script (`scripts/codex_delegate.py`) provides one deterministic boundary for:

- Flag parsing and validation
- Prompt credential scanning (pre-dispatch)
- `codex exec` subprocess invocation
- JSONL event stream parsing
- Session/thread ID extraction
- Analytics event emission

The skill's only job is to: parse user arguments, write input JSON, run the adapter, review changes, report results.

### Clean-tree gate

`codex exec` modifies the working tree. Reliable diff attribution requires knowing what Codex changed vs. what was already dirty. Step 1 enforces a clean-tree precondition — the adapter checks `git status --porcelain` and fails deterministically if the tree is dirty.

Future steps add worktree-based execution (create a disposable worktree, run Codex there, review changes, merge or discard).

---

## Deliverables

### 1. Shared event log helper (`scripts/event_log.py`)

Extract duplicated log infrastructure into a shared module. Currently duplicated across `codex_guard.py` and `emit_analytics.py`.

**Exports:**

```python
LOG_PATH: Path          # ~/.claude/.codex-events.jsonl
def ts() -> str         # ISO 8601 UTC with Z suffix
def append_log(entry: dict) -> bool  # Atomic append, returns success
def session_id() -> str | None       # From CLAUDE_SESSION_ID, nullable, never fabricated
```

**Migration:** Update `codex_guard.py` and `emit_analytics.py` to import from `event_log.py`. No behavior changes.

### 2. Adapter script (`scripts/codex_delegate.py`)

Single entry point for all delegation. Claude makes one Bash call; the adapter handles everything.

#### Input

JSON file with fields:

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `prompt` | string | Yes (fresh) | — |
| `model` | string | No | Codex default |
| `sandbox` | enum | No | `workspace-write` |
| `reasoning_effort` | enum | No | `high` |
| `full_auto` | bool | No | `false` |
| `resume_last` | bool | No | `false` |

**Sandbox values:** `read-only`, `workspace-write`. `danger-full-access` is rejected in Step 1.

**Resume constraints:** When `resume_last=true`, `prompt` is optional (stdin prompt), `-m` is supported, `-s` is not (Codex CLI limitation). Fields `sandbox`, `reasoning_effort`, `full_auto` are ignored on resume.

#### Pipeline

```
1. Read input JSON
2. Validate fields (reject unknown, check enums, check conflicts)
3. Conflict check: --full-auto + -s read-only → deterministic error
4. Clean-tree gate: git status --porcelain → block if dirty (list dirty paths)
5. Credential scan: strict + contextual tiers from codex_guard.py patterns
   → block on match (log block event)
6. Build codex exec command:
   - codex exec --json -o /tmp/codex_delegate_output_{uuid}.txt
   - Resolved flags: -s, -m, -c model_reasoning_effort=..., --full-auto
   - No --skip-git-repo-check (Codex's own repo guard is additive safety)
7. Run subprocess, capture JSONL stdout + exit code
8. Parse JSONL events:
   - thread.started → extract thread_id
   - item.completed → collect commands_run (type=command_execution)
   - turn.completed → extract token_usage (nullable)
   - error → capture error details
9. Read -o output file → summary (nullable)
10. Emit delegation_outcome event to log
11. Return structured JSON to stdout
```

#### Output

```json
{
  "status": "ok|error|blocked",
  "thread_id": "...",
  "summary": null,
  "commands_run": [
    {"command": "...", "exit_code": 0}
  ],
  "exit_code": 0,
  "token_usage": null,
  "error": null
}
```

`summary` is nullable — a failing run may not produce a final assistant message. `token_usage` is nullable — an erroring run may not emit `turn.completed`.

**Status values:**

| Status | Meaning |
|--------|---------|
| `ok` | `codex exec` completed (exit code may still be non-zero) |
| `blocked` | Pre-dispatch gate failed (credential match or dirty tree) |
| `error` | Adapter-level failure (bad input, subprocess crash, parse failure) |

#### Error format

All errors follow the project convention:
`"{operation} failed: {reason}. Got: {input!r:.100}"`

#### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success or blocked (check `status` field) |
| 1 | Adapter error (bad input, internal failure) |

Exit 0 for blocked is intentional — the adapter communicated the block cleanly via structured output. Exit 1 means the adapter itself failed.

### 3. Delegation skill (`skills/delegate/SKILL.md`)

#### Frontmatter

```yaml
---
name: delegate
description: >-
  Delegate coding tasks to Codex CLI for autonomous execution.
  Use when user says "delegate", "have codex do", "codex exec",
  "run this with codex", or wants Codex to write code, fix bugs,
  or refactor autonomously. Not for consultation — use /codex
  or /dialogue for second opinions.
argument-hint: "[-m <model>] [-s {read-only|workspace-write}] [-t {minimal|low|medium|high|xhigh}] [--full-auto] [--resume] PROMPT"
user-invocable: true
---
```

#### Skill flow

```
1. Parse flags from $ARGUMENTS:
   -m <model>           → model (optional)
   -s <sandbox>         → sandbox (default: workspace-write)
   -t <effort>          → reasoning_effort (default: high)
   --full-auto          → full_auto (requires explicit flag)
   --resume             → resume_last (mutually exclusive with fresh flags)

2. Validate:
   - --full-auto + -s read-only → error
   - danger-full-access → error ("not supported in this version")
   - --resume with -s → error ("-s not supported on resume")

3. Write input JSON to $TMPDIR/codex_delegate_input_{random}.json

4. Run adapter:
   python3 {plugin_root}/scripts/codex_delegate.py $TMPDIR/codex_delegate_input_{random}.json

5. Read adapter output. Branch on status:
   - blocked → relay block reason to user
   - error → relay error to user
   - ok → proceed to review

6. Review changes:
   - Run: git status --short
   - Run: git diff (for modified files)
   - Present summary: what Codex did, which files changed, commands it ran
   - Claude's own assessment of the changes (quality, correctness, completeness)

7. Report to user:
   - Codex's summary (from adapter output)
   - Files changed (from git status --short)
   - Claude's assessment
   - Thread ID for potential resume
```

#### Governance

1. **No auto-escalation:** `danger-full-access` is blocked entirely in Step 1.
2. **`--full-auto` is opt-in only:** Never auto-enable. Never "offer" it implicitly. Requires explicit user flag.
3. **Clean tree required:** Delegation fails deterministically on dirty trees.
4. **Credential scan is fail-closed:** If scan cannot complete, block dispatch.
5. **Claude reviews all changes:** The skill always runs `git status --short` after delegation and presents Claude's assessment before considering the task complete.

### 4. Analytics event (`delegation_outcome`)

New event type in the JSONL log.

```json
{
  "schema_version": "0.1.0",
  "event": "delegation_outcome",
  "ts": "2026-03-06T12:00:00Z",
  "consultation_id": "uuid",
  "session_id": "from-env-or-null",
  "thread_id": "from-codex-jsonl",
  "sandbox": "workspace-write",
  "model": null,
  "reasoning_effort": "high",
  "full_auto": false,
  "resume": false,
  "credential_blocked": false,
  "dirty_tree_blocked": false,
  "commands_run_count": 3,
  "exit_code": 0,
  "termination_reason": "complete"
}

```

**`termination_reason` values:** `complete`, `error`, `blocked`

**`session_id` contract:** Nullable, never fabricated. Read from `CLAUDE_SESSION_ID` environment variable. Absent or whitespace-only → `null`. Mirrors `emit_analytics.py` behavior exactly.

**Emission:** The adapter writes directly to `~/.claude/.codex-events.jsonl` via the shared `event_log.py` helper. No routing through `emit_analytics.py` — delegation events don't need synthesis parsing or convergence mapping.

### 5. Event reader update (`read_events.py`)

Add `delegation_outcome` to `_KNOWN_UNSTRUCTURED` set. This prevents `--validate` from reporting delegation events as unknown.

```python
_KNOWN_UNSTRUCTURED = {"block", "shadow", "consultation", "delegation_outcome"}
```

Full schema validation for `delegation_outcome` (like `dialogue_outcome` has) is deferred until the event shape stabilizes after real usage.

---

## Credential Scanning

The adapter reuses the pattern lists from `codex_guard.py` (strict + contextual tiers). This is the same credential detection that guards MCP-based consultation, applied to the delegation prompt before it reaches `codex exec`.

**Why not a Bash PreToolUse hook?** The existing hook infrastructure only matches the two Codex MCP tools. A Bash PreToolUse hook would fire on every Bash call — not just delegation. The adapter-level scan is more precise: it only runs when delegation is the intent.

Step 2 of the roadmap adds a Bash hook or adapter-level credential scan for users who run `codex exec` manually (outside the `/delegate` skill). That's a separate concern.

---

## Codex CLI Surface (verified against codex-cli 0.111.0)

### `codex exec` flags

| Flag | Supported | Notes |
|------|-----------|-------|
| `--json` | Yes | JSONL output with `thread.started`, `turn.*`, `item.*`, `error` events |
| `-o / --output-last-message` | Yes | Writes final assistant message to file |
| `-m / --model` | Yes | Model selection |
| `-s / --sandbox` | Yes | `read-only`, `workspace-write`, `danger-full-access` |
| `-c key=value` | Yes | Config overrides (used for `model_reasoning_effort`) |
| `--full-auto` | Yes | Convenience alias: `-s workspace-write` + approval `on-request` |
| `--skip-git-repo-check` | Yes | **Not used** — adapter requires git repo |
| `-a / --ask-for-approval` | **No** | Not available in exec mode |

### `codex exec resume` flags

| Flag | Supported | Notes |
|------|-----------|-------|
| `--last` | Yes | Resume most recent session |
| `--json` | Yes | JSONL output |
| `-o` | Yes | Output file |
| `-m` | Yes | Model selection |
| `--full-auto` | Yes | Auto-approve |
| `-s / --sandbox` | **No** | Not available on resume |

### JSONL event families (from official docs)

| Event type | Key fields | Adapter use |
|------------|-----------|-------------|
| `thread.started` | `thread_id` | Extract thread ID |
| `turn.started` | — | Ignored |
| `turn.completed` | `usage.input_tokens`, `usage.output_tokens` | Token usage (nullable) |
| `item.started` | `item.type`, `item.command` | Ignored |
| `item.completed` | `item.type`, `item.command`, `item.exit_code`, `item.text` | Commands run, messages |
| `error` | Error details | Capture for reporting |

---

## What This Spec Does NOT Cover

These are explicitly deferred to future steps:

| Step | Capability | Depends on |
|------|-----------|------------|
| 2 | Bash PreToolUse hook for manual `codex exec` calls | Step 1 deployed |
| 3 | Dirty-tree gating with temp-worktree execution | Step 1 deployed |
| 4 | MCP server wrapping `codex exec` (typed delegation tools) | Other skills/agents needing typed calls |
| 5 | `codex-executor` agent (orchestrated multi-step delegation) | Stable transport contract from Steps 1-4 |

---

## Decision Log

| # | Decision | Rationale | Source |
|---|----------|-----------|--------|
| D1 | Separate `/delegate` verb, not `--exec` on `/codex` | `/codex` is hardwired to consultation analytics; mixing paradigms muddies safety model | Design discussion |
| D2 | Adapter script, not raw Bash in skill | One deterministic boundary for flag parsing, credential scan, JSONL capture, analytics | User (hybrid proposal) |
| D3 | Clean-tree hard requirement (Step 1) | Warning-only defeats reliable diff attribution; worktree support deferred to Step 3 | Codex consultation 1 |
| D4 | `workspace-write` default sandbox | Delegation implies execution; `read-only` is explicit opt-in for analysis-only | Codex consultation 1 |
| D5 | Block `danger-full-access` in Step 1 | Defer until stronger controls exist; official docs label it elevated risk | Codex consultation 1 |
| D6 | `--full-auto` requires explicit user flag | Never auto-enable, never offer implicitly; `--full-auto` + `-s read-only` is a deterministic error | Codex consultation 1 |
| D7 | Drop `--skip-git-repo-check` | Adapter requires git repo for clean-tree gate and diff review; Codex's own repo guard is additive | Codex consultation 2 |
| D8 | `thread_id` canonical, no `session_id` from JSONL | Docs document `thread_id` in JSONL; no documented `session_id` in event stream | Codex consultation 2 |
| D9 | `files_changed` from `git status --short`, not JSONL | JSONL shows commands, not authoritative file state; `git status --short` also catches new untracked files | Codex consultation 2 |
| D10 | Add `delegation_outcome` to `read_events.py` `_KNOWN_UNSTRUCTURED` | Prevents false validation errors on `--validate`; full schema validation deferred | Codex consultation 2 |
| D11 | Shared `event_log.py` module | Prevents third duplication of `_append_log` / `_ts` / `_session_id` across adapter, guard, and emitter | Codex consultation 2 |
| D12 | `summary` and `token_usage` nullable in adapter output | Docs guarantee JSONL event families, not that every run produces a final message or completed turn | Codex consultation 2 |
| D13 | Resume supports `-m` but not `-s` | Verified against CLI help for `codex exec resume` | Codex consultation 1 |

---

## File Manifest

| File | Action | Purpose |
|------|--------|---------|
| `scripts/event_log.py` | Create | Shared event log helper (extracted from existing scripts) |
| `scripts/codex_delegate.py` | Create | Delegation adapter script |
| `skills/delegate/SKILL.md` | Create | `/delegate` skill |
| `scripts/codex_guard.py` | Edit | Import from `event_log.py` instead of local `_append_log`/`_ts` |
| `scripts/emit_analytics.py` | Edit | Import from `event_log.py` instead of local `_append_log`/`_ts`/`_session_id` |
| `scripts/read_events.py` | Edit | Add `delegation_outcome` to `_KNOWN_UNSTRUCTURED` |

All paths relative to `packages/plugins/cross-model/`.
